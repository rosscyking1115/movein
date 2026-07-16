import { describe, expect, it } from "vitest";
import cases from "../../../contracts/neighbourhood-scoring-v2-cases.json";
import { evidenceQuality, matchScore, reweight } from "./reweight";
import type { Area, ComponentKey } from "./types";

describe("scoring contract v2 golden cases", () => {
  for (const testCase of cases.cases) {
    it(testCase.name, () => {
      const area = testCase.scores as unknown as Area;
      const supplied = testCase.weights as Partial<Record<ComponentKey, number>>;
      const weights = Object.fromEntries(
        (Object.keys(testCase.scores) as ComponentKey[]).map((key) => [
          key,
          Object.keys(supplied).length === 0 ? 1 : supplied[key] ?? 0,
        ]),
      ) as Record<ComponentKey, number>;
      expect(matchScore(area, weights)).toBe(testCase.expected);
    });
  }

  for (const testCase of cases.evidence_cases) {
    it(testCase.name, () => {
      expect(evidenceQuality(testCase.inputs)).toBe(testCase.expected);
    });
  }

  for (const testCase of cases.ranking_cases) {
    it(testCase.name, () => {
      const areas = testCase.areas.map(({ area_id, score }) => ({
        area_id,
        affordability_score: score,
        safety_score: score,
        energy_score: score,
        flood_score: score,
        convenience_score: score,
      })) as Area[];
      const weights = Object.fromEntries(
        (Object.keys(cases.cases[0].scores) as ComponentKey[]).map((key) => [key, 1]),
      ) as Record<ComponentKey, number>;
      expect(reweight(areas, weights).map((area) => area.area_id)).toEqual(
        testCase.expected_area_ids,
      );
    });
  }
});
