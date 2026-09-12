import { readFile, writeFile } from "node:fs/promises";
import openapiTS, { astToString } from "openapi-typescript";
import prettier from "prettier";

const schema = new URL("../../../docs/openapi.json", import.meta.url);
const destination = new URL("../lib/generated.ts", import.meta.url);
const generated = astToString(await openapiTS(schema));
const formatted = await prettier.format(generated, { parser: "typescript" });
if (process.argv.includes("--check")) {
  const current = await readFile(destination, "utf8");
  if (current !== formatted) {
    throw new Error(
      "Generated frontend contract differs from OpenAPI. Run contract:generate.",
    );
  }
  console.log("Frontend contract matches generated OpenAPI.");
} else {
  await writeFile(destination, formatted);
  console.log("Frontend contract generated from OpenAPI.");
}
