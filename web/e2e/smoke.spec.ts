// The pages a visitor and a researcher meet first: they load, show their heading and throw no uncaught errors
// (a failed call to the analysis engine is fine here; an exception in the page is not).
import fs from "node:fs";
import path from "node:path";
import { expect, test, type Page } from "@playwright/test";

type Post = { slug: string; title: string; title_en?: string; body_en?: string };
const posts: Post[] = JSON.parse(fs.readFileSync(path.join(process.cwd(), "content", "articles.json"), "utf-8")).posts;

function watchErrors(page: Page): string[] {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(e.message));
  return errors;
}

test("startsidan", async ({ page }) => {
  const errors = watchErrors(page);
  await page.goto("/");
  await expect(page.getByRole("heading", { level: 1 })).toContainText("En öppen forskningsplattform");
  expect(errors).toEqual([]);
});

test("artikellistan", async ({ page }) => {
  const errors = watchErrors(page);
  await page.goto("/artiklar/");
  await expect(page.getByRole("heading", { level: 1 })).toHaveText("Mönster i runstenarna");
  await expect(page.locator(`a[href*="/artiklar/${posts[0].slug}"]`).first()).toBeVisible();
  expect(errors).toEqual([]);
});

test("en artikel på svenska", async ({ page }) => {
  const errors = watchErrors(page);
  const p = posts[0];
  await page.goto(`/artiklar/${p.slug}/`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(p.title);
  await expect(page.getByText("Det viktigaste i korthet").first()).toBeVisible();
  expect(errors).toEqual([]);
});

test("samma artikel på engelska", async ({ page }) => {
  const errors = watchErrors(page);
  const p = posts.find((x) => x.body_en && x.title_en);
  test.skip(!p, "ingen artikel har en engelsk utgåva");
  await page.goto(`/en/artiklar/${p!.slug}/`);
  await expect(page.getByRole("heading", { level: 1 })).toHaveText(p!.title_en!);
  expect(errors).toEqual([]);
});

test("3D-sidan", async ({ page }) => {
  const errors = watchErrors(page);
  await page.goto("/3d");
  await expect(page.getByRole("heading", { level: 2 }).first()).toBeVisible();
  await expect(page.locator('input[type="file"]').first()).toBeAttached();
  expect(errors).toEqual([]);
});
