"use client";

import { useCallback, useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  APIProvider,
  Map as GoogleMap,
  AdvancedMarker,
  InfoWindow,
  useMap,
} from "@vis.gl/react-google-maps";
import { MarkerClusterer, SuperClusterAlgorithm } from "@googlemaps/markerclusterer";
import type { Marker, Renderer } from "@googlemaps/markerclusterer";
import type { Area } from "@/lib/types";
import { areaSlug } from "@/lib/slug";
import { score as fmtScore, rentPerMonth } from "@/lib/format";

const API_KEY = process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY;
// AdvancedMarkers (and cloud styling) need a Map ID. DEMO_MAP_ID works for dev;
// create your own in Google Cloud → Map Management for production styling.
const MAP_ID = process.env.NEXT_PUBLIC_GOOGLE_MAPS_MAP_ID ?? "DEMO_MAP_ID";

type Props = {
  areas: Area[];
  selected: Area | null;
  onSelect: (area: Area | null) => void;
};

const withCoords = (areas: Area[]) =>
  areas.filter((a) => a.latitude != null && a.longitude != null);

const latLng = (a: Area) => ({ lat: a.latitude as number, lng: a.longitude as number });

// Clean, brand-coloured cluster bubbles (replaces the default red/blue gradient).
const clusterRenderer: Renderer = {
  render: ({ count, position }) => {
    const size = count < 10 ? 34 : count < 50 ? 42 : 50;
    const el = document.createElement("div");
    el.textContent = String(count);
    el.style.cssText = `display:flex;align-items:center;justify-content:center;
      width:${size}px;height:${size}px;border-radius:9999px;
      background:var(--accent,#13476b);color:#fff;
      font:600 ${count < 50 ? 13 : 14}px/1 system-ui,-apple-system,sans-serif;
      border:2px solid #fff;box-shadow:0 1px 6px rgba(0,0,0,.32);cursor:pointer;`;
    return new google.maps.marker.AdvancedMarkerElement({
      position,
      content: el,
      zIndex: 1000 + count,
    });
  },
};

export default function SearchMap({ areas, selected, onSelect }: Props) {
  if (!API_KEY) {
    return (
      <div className="flex h-[380px] w-full flex-col items-center justify-center gap-1.5 rounded-[14px] border border-dashed border-rule2 bg-card2 p-6 text-center">
        <p className="text-sm font-semibold text-ink">Map needs a Google Maps API key</p>
        <p className="max-w-[420px] text-[13px] text-muted">
          Add <code className="font-mono text-ink2">NEXT_PUBLIC_GOOGLE_MAPS_API_KEY</code> to{" "}
          <code className="font-mono text-ink2">web/.env.local</code> and restart the dev server.
          The results list below works without it.
        </p>
      </div>
    );
  }

  return (
    <APIProvider apiKey={API_KEY}>
      <GoogleMap
        mapId={MAP_ID}
        defaultCenter={{ lat: 52.8, lng: -1.8 }}
        defaultZoom={6}
        gestureHandling="greedy"
        clickableIcons={false}
        disableDefaultUI={false}
        mapTypeControl={false}
        streetViewControl={false}
        fullscreenControl={false}
        className="h-[380px] w-full overflow-hidden rounded-[14px] border border-rule2"
      >
        <MarkerLayer areas={areas} selected={selected} onSelect={onSelect} />
      </GoogleMap>
    </APIProvider>
  );
}

function MarkerLayer({ areas, selected, onSelect }: Props) {
  const map = useMap();
  const router = useRouter();
  const pts = useMemo(() => withCoords(areas), [areas]);
  // Identity of the current pin SET (region/budget), stable across slider re-ranks.
  const idKey = useMemo(() => pts.map((a) => a.area_id).sort().join(","), [pts]);

  // Collect marker DOM elements in a ref (not state) so attaching them never
  // triggers a re-render — a state update here would loop with the ref callbacks.
  const markersRef = useRef<Map<string, Marker>>(new Map());
  const clusterer = useRef<MarkerClusterer | null>(null);

  // Sync the clusterer from the ref callbacks, coalesced into one rAF pass.
  // Markers attach asynchronously (after Google's marker library loads), so an
  // effect keyed on the pin set fires too early and clusters an empty list —
  // driving the sync from the attach itself is the only reliable timing.
  const rafId = useRef<number | null>(null);
  const syncedKey = useRef("");
  const scheduleClusterSync = useCallback(() => {
    if (rafId.current != null) return;
    rafId.current = requestAnimationFrame(() => {
      rafId.current = null;
      const c = clusterer.current;
      if (!c) return;
      const key = [...markersRef.current.keys()].sort().join(",");
      if (key === syncedKey.current) return;
      syncedKey.current = key;
      c.clearMarkers();
      c.addMarkers([...markersRef.current.values()]);
    });
  }, []);

  const setMarkerRef = useCallback(
    (id: string, marker: Marker | null) => {
      if (marker) markersRef.current.set(id, marker);
      else markersRef.current.delete(id);
      scheduleClusterSync();
    },
    [scheduleClusterSync],
  );

  useEffect(() => {
    if (!map || clusterer.current) return;
    clusterer.current = new MarkerClusterer({
      map,
      renderer: clusterRenderer,
      // Pills are ~36px wide, so cluster on a wider radius than the default 60
      // or neighbouring pills overlap without ever grouping.
      algorithm: new SuperClusterAlgorithm({ radius: 90, maxZoom: 15 }),
    });
    scheduleClusterSync();
    return () => {
      if (rafId.current != null) cancelAnimationFrame(rafId.current);
      rafId.current = null;
      clusterer.current?.clearMarkers();
      clusterer.current = null;
      syncedKey.current = "";
    };
  }, [map, scheduleClusterSync]);

  // Fit the view to the pins, but only when the SET changes (region/budget),
  // not on every slider re-rank — refitting each tick is jarring.
  const lastKey = useRef("");
  useEffect(() => {
    if (!map) return;
    if (idKey === lastKey.current) return;
    lastKey.current = idKey;
    if (!pts.length) return;
    const bounds = new google.maps.LatLngBounds();
    pts.forEach((a) => bounds.extend(latLng(a)));
    map.fitBounds(bounds, 36);
  }, [map, pts, idKey]);

  // Pan to (and zoom toward) the selected area when it changes.
  useEffect(() => {
    if (!map || !selected || selected.latitude == null) return;
    map.panTo(latLng(selected));
    if ((map.getZoom() ?? 0) < 11) map.setZoom(12);
  }, [map, selected]);

  return (
    <>
      {pts.map((a) => {
        const isSel = selected?.area_id === a.area_id;
        return (
          <AdvancedMarker
            key={a.area_id}
            position={latLng(a)}
            ref={(marker) => setMarkerRef(a.area_id, marker)}
            onClick={() => onSelect(a)}
            zIndex={isSel ? 9999 : undefined}
            title={`${a.area_name} · ${fmtScore(a.match_score ?? a.overall_score)}/100`}
          >
            {/* Google-Hotels-style price pill: shows the match score, with a tail. */}
            <div
              className={`relative cursor-pointer select-none rounded-full px-2.5 py-[3px] text-[12px] font-semibold leading-none shadow-[0_1px_5px_rgba(0,0,0,.3)] transition-transform hover:scale-110
                after:absolute after:left-1/2 after:top-full after:-mt-[3px] after:h-[7px] after:w-[7px] after:-translate-x-1/2 after:rotate-45 after:content-['']
                ${
                  isSel
                    ? "z-10 scale-110 bg-accent text-white after:bg-accent"
                    : "border border-rule2 bg-card text-ink after:border-b after:border-r after:border-rule2 after:bg-card"
                }`}
            >
              {fmtScore(a.match_score ?? a.overall_score)}
            </div>
          </AdvancedMarker>
        );
      })}

      {selected && selected.latitude != null && (
        <InfoWindow position={latLng(selected)} onCloseClick={() => onSelect(null)} headerDisabled>
          <div className="relative min-w-[220px] max-w-[260px] p-1 font-sans">
            <button
              type="button"
              onClick={() => onSelect(null)}
              aria-label="Close"
              className="absolute -right-0.5 -top-0.5 flex h-6 w-6 cursor-pointer items-center justify-center rounded-full text-[18px] leading-none text-[#6b7a82] transition-colors hover:bg-[#eceee9] hover:text-[#172026]"
            >
              ×
            </button>
            <div className="pr-6 text-[16px] font-bold leading-tight text-[#172026]">{selected.area_name}</div>
            <div className="mt-0.5 text-[12px] text-[#6b7a82]">
              {[selected.local_authority_name, selected.region].filter(Boolean).join(" · ")}
            </div>
            <div className="mt-2 flex items-baseline gap-3">
              <div>
                <span className="font-mono text-[26px] font-medium leading-none text-[#172026]">
                  {fmtScore(selected.match_score ?? selected.overall_score)}
                </span>
                <span className="ml-0.5 text-[12px] text-[#6b7a82]">/100 match</span>
              </div>
              {selected.official_rent_monthly_gbp != null && (
                <div className="text-[12px] text-[#3c4a52]">{rentPerMonth(selected.official_rent_monthly_gbp)}</div>
              )}
            </div>
            <button
              type="button"
              onClick={() => router.push(`/area/${areaSlug(selected.area_id, selected.area_name)}`)}
              className="mt-2.5 w-full cursor-pointer rounded-[8px] bg-[#13476b] px-3 py-1.5 text-center text-[13px] font-semibold text-white transition-opacity hover:opacity-90"
            >
              Show details →
            </button>
          </div>
        </InfoWindow>
      )}
    </>
  );
}
