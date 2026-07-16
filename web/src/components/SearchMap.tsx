"use client";

import { useEffect, useMemo, useRef } from "react";
import { useRouter } from "next/navigation";
import maplibregl, { type GeoJSONSource, type MapLayerMouseEvent } from "maplibre-gl";
import type { Feature, FeatureCollection, Point } from "geojson";
import type { Area } from "@/lib/types";
import { areaSlug } from "@/lib/slug";
import { score as fmtScore, rentPerMonth } from "@/lib/format";

const MAP_STYLE = "https://tiles.openfreemap.org/styles/positron";
const SOURCE_ID = "housing-areas";
const CLUSTER_LAYER = "area-clusters";
const CLUSTER_COUNT_LAYER = "area-cluster-count";
const POINT_LAYER = "area-points";
const SCORE_LAYER = "area-score-labels";

type Props = {
  areas: Area[];
  selected: Area | null;
  onSelect: (area: Area | null) => void;
};

type AreaProperties = {
  area_id: string;
  score_label: string;
};

const withCoords = (areas: Area[]) =>
  areas.filter((area) => area.latitude != null && area.longitude != null);

export const toFeatureCollection = (
  areas: Area[],
): FeatureCollection<Point, AreaProperties> => ({
  type: "FeatureCollection",
  features: withCoords(areas).map(
    (area): Feature<Point, AreaProperties> => ({
      type: "Feature",
      geometry: {
        type: "Point",
        coordinates: [area.longitude as number, area.latitude as number],
      },
      properties: {
        area_id: area.area_id,
        score_label: fmtScore(area.match_score ?? area.overall_score),
      },
    }),
  ),
});

function fitToAreas(map: maplibregl.Map, areas: Area[]) {
  const points = withCoords(areas);
  if (!points.length) return;

  const bounds = new maplibregl.LngLatBounds();
  points.forEach((area) => bounds.extend([area.longitude as number, area.latitude as number]));
  map.fitBounds(bounds, { padding: 36, maxZoom: 12, duration: 0 });
}

export default function SearchMap({ areas, selected, onSelect }: Props) {
  const router = useRouter();
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<maplibregl.Map | null>(null);
  const areasRef = useRef(new Map<string, Area>());
  const onSelectRef = useRef(onSelect);
  const idKey = useMemo(
    () => withCoords(areas).map((area) => area.area_id).sort().join(","),
    [areas],
  );

  useEffect(() => {
    areasRef.current = new Map(areas.map((area) => [area.area_id, area]));
    onSelectRef.current = onSelect;
  }, [areas, onSelect]);

  useEffect(() => {
    if (!containerRef.current) return;

    const map = new maplibregl.Map({
      container: containerRef.current,
      style: MAP_STYLE,
      center: [-1.8, 52.8],
      zoom: 5.2,
      attributionControl: {},
    });
    mapRef.current = map;
    map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    const selectPoint = (event: MapLayerMouseEvent) => {
      const areaId = event.features?.[0]?.properties?.area_id;
      if (typeof areaId === "string") {
        onSelectRef.current(areasRef.current.get(areaId) ?? null);
      }
    };

    const expandCluster = async (event: MapLayerMouseEvent) => {
      const feature = event.features?.[0];
      const clusterId = feature?.properties?.cluster_id;
      const coordinates = (feature?.geometry as Point | undefined)?.coordinates;
      const source = map.getSource(SOURCE_ID) as GeoJSONSource | undefined;
      if (typeof clusterId !== "number" || !coordinates || !source) return;

      const zoom = await source.getClusterExpansionZoom(clusterId);
      map.easeTo({ center: coordinates as [number, number], zoom });
    };

    const showPointer = () => {
      map.getCanvas().style.cursor = "pointer";
    };
    const resetPointer = () => {
      map.getCanvas().style.cursor = "";
    };

    map.on("load", () => {
      map.addSource(SOURCE_ID, {
        type: "geojson",
        data: toFeatureCollection(Array.from(areasRef.current.values())),
        cluster: true,
        clusterMaxZoom: 15,
        clusterRadius: 90,
      });

      map.addLayer({
        id: CLUSTER_LAYER,
        type: "circle",
        source: SOURCE_ID,
        filter: ["has", "point_count"],
        paint: {
          "circle-color": "#13476b",
          "circle-radius": ["step", ["get", "point_count"], 18, 10, 22, 50, 26],
          "circle-stroke-color": "#ffffff",
          "circle-stroke-width": 2,
        },
      });
      map.addLayer({
        id: CLUSTER_COUNT_LAYER,
        type: "symbol",
        source: SOURCE_ID,
        filter: ["has", "point_count"],
        layout: {
          "text-field": ["get", "point_count_abbreviated"],
          "text-font": ["Noto Sans Regular"],
          "text-size": 13,
        },
        paint: { "text-color": "#ffffff" },
      });
      map.addLayer({
        id: POINT_LAYER,
        type: "circle",
        source: SOURCE_ID,
        filter: ["!", ["has", "point_count"]],
        paint: {
          "circle-color": "#ffffff",
          "circle-radius": 15,
          "circle-stroke-color": "#5f707a",
          "circle-stroke-width": 1.5,
        },
      });
      map.addLayer({
        id: SCORE_LAYER,
        type: "symbol",
        source: SOURCE_ID,
        filter: ["!", ["has", "point_count"]],
        layout: {
          "text-field": ["get", "score_label"],
          "text-font": ["Noto Sans Regular"],
          "text-size": 11,
        },
        paint: { "text-color": "#172026" },
      });

      map.on("click", CLUSTER_LAYER, expandCluster);
      map.on("click", POINT_LAYER, selectPoint);
      map.on("click", SCORE_LAYER, selectPoint);
      [CLUSTER_LAYER, POINT_LAYER, SCORE_LAYER].forEach((layer) => {
        map.on("mouseenter", layer, showPointer);
        map.on("mouseleave", layer, resetPointer);
      });
      fitToAreas(map, Array.from(areasRef.current.values()));
    });

    return () => {
      map.remove();
      mapRef.current = null;
    };
  }, []);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.isStyleLoaded()) return;
    const source = map.getSource(SOURCE_ID) as GeoJSONSource | undefined;
    source?.setData(toFeatureCollection(areas));
  }, [areas]);

  // Keep the viewport stable while slider weights only re-rank/relabel the same
  // areas; refit only when the actual result set changes.
  useEffect(() => {
    const map = mapRef.current;
    if (!map?.isStyleLoaded()) return;
    fitToAreas(map, Array.from(areasRef.current.values()));
  }, [idKey]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map?.isStyleLoaded() || !map.getLayer(POINT_LAYER)) return;

    const selectedId = selected?.area_id ?? "";
    map.setPaintProperty(POINT_LAYER, "circle-color", [
      "case",
      ["==", ["get", "area_id"], selectedId],
      "#13476b",
      "#ffffff",
    ]);
    map.setPaintProperty(SCORE_LAYER, "text-color", [
      "case",
      ["==", ["get", "area_id"], selectedId],
      "#ffffff",
      "#172026",
    ]);

    if (selected?.longitude != null && selected.latitude != null) {
      map.easeTo({
        center: [selected.longitude, selected.latitude],
        zoom: Math.max(map.getZoom(), 11),
      });
    }
  }, [selected]);

  return (
    <div className="relative h-[380px] w-full overflow-hidden rounded-[14px] border border-rule2">
      <div
        ref={containerRef}
        role="region"
        aria-label="Map of search result areas"
        className="h-full w-full"
      />

      {selected && selected.latitude != null && (
        <div
          aria-live="polite"
          aria-atomic="true"
          className="absolute bottom-3 left-3 z-10 min-w-[220px] max-w-[calc(100%_-_1.5rem)] rounded-[10px] border border-rule2 bg-card p-3 shadow-lg"
        >
          <button
            type="button"
            onClick={() => onSelect(null)}
            aria-label="Close map details"
            className="absolute right-2 top-2 flex h-6 w-6 cursor-pointer items-center justify-center rounded-full text-[18px] leading-none text-muted transition-colors hover:bg-card2 hover:text-ink"
          >
            ×
          </button>
          <div className="pr-6 text-[16px] font-bold leading-tight text-ink">{selected.area_name}</div>
          <div className="mt-0.5 text-[12px] text-muted">
            {[selected.local_authority_name, selected.region].filter(Boolean).join(" · ")}
          </div>
          <div className="mt-2 flex items-baseline gap-3">
            <div>
              <span className="font-mono text-[26px] font-medium leading-none text-ink">
                {fmtScore(selected.match_score ?? selected.overall_score)}
              </span>
              <span className="ml-0.5 text-[12px] text-muted">/100 match</span>
            </div>
            {selected.official_rent_monthly_gbp != null && (
              <div className="text-[12px] text-ink2">
                {rentPerMonth(selected.official_rent_monthly_gbp)}
              </div>
            )}
          </div>
          <button
            type="button"
            onClick={() => router.push(`/area/${areaSlug(selected.area_id, selected.area_name)}`)}
            className="mt-2.5 w-full cursor-pointer rounded-[8px] bg-accent px-3 py-1.5 text-center text-[13px] font-semibold text-white transition-opacity hover:opacity-90"
          >
            Show details →
          </button>
        </div>
      )}
    </div>
  );
}
