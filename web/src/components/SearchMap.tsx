"use client";

import { useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import { MapContainer, TileLayer, CircleMarker, Tooltip, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";
import type { Area } from "@/lib/types";
import { areaSlug } from "@/lib/slug";
import { score as fmtScore } from "@/lib/format";

// Fit the view to the current pins, but only when the SET of areas changes
// (region/budget), not on every slider re-rank — refitting on each tick is jarring.
function FitBounds({ areas }: { areas: Area[] }) {
  const map = useMap();
  const lastKey = useRef("");
  useEffect(() => {
    const key = areas.map((a) => a.area_id).sort().join(",");
    if (key === lastKey.current) return;
    lastKey.current = key;
    const pts = areas.map((a) => [a.latitude as number, a.longitude as number] as [number, number]);
    if (pts.length) map.fitBounds(L.latLngBounds(pts), { padding: [28, 28], maxZoom: 12 });
  }, [areas, map]);
  return null;
}

export default function SearchMap({ areas }: { areas: Area[] }) {
  const router = useRouter();
  const pts = useMemo(() => areas.filter((a) => a.latitude != null && a.longitude != null), [areas]);

  return (
    <MapContainer
      center={[52.8, -1.8]}
      zoom={6}
      scrollWheelZoom={false}
      className="h-[380px] w-full overflow-hidden rounded-[14px] border border-rule2"
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://tile.openstreetmap.org/{z}/{x}/{y}.png"
      />
      <FitBounds areas={pts} />
      {pts.map((a) => {
        const s = a.match_score ?? a.overall_score;
        const slug = areaSlug(a.area_id, a.area_name);
        return (
          <CircleMarker
            key={a.area_id}
            center={[a.latitude as number, a.longitude as number]}
            radius={7}
            pathOptions={{ color: "#0d3550", weight: 1.5, fillColor: "#13476b", fillOpacity: 0.7 }}
            eventHandlers={{
              click: () => router.push(`/area/${slug}`),
              mouseover: (e) => e.target.setStyle({ fillOpacity: 1, radius: 9 }),
              mouseout: (e) => e.target.setStyle({ fillOpacity: 0.7, radius: 7 }),
            }}
          >
            <Tooltip direction="top" offset={[0, -4]}>
              <span style={{ fontWeight: 600 }}>{a.area_name}</span> · {fmtScore(s)}/100
            </Tooltip>
          </CircleMarker>
        );
      })}
    </MapContainer>
  );
}
