import enStrings from "./en.json";
import itStrings from "./it.json";

function keys(obj: object, prefix = ""): string[] {
  return Object.entries(obj).flatMap(([key, value]) =>
    typeof value === "object" && value !== null
      ? keys(value as object, `${prefix}${key}.`)
      : [`${prefix}${key}`],
  );
}

it("en.json mirrors every key of it.json", () => {
  expect(keys(enStrings).sort()).toEqual(keys(itStrings).sort());
});
