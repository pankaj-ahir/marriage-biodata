import type { Metadata } from "next";
import Header from "@/components/Header";
import TemplateGallery from "@/components/TemplateGallery";
import { TEMPLATES } from "@/lib/templates";
import { SITE_NAME } from "@/lib/site";

export const metadata: Metadata = {
  title: "All Marriage Biodata Templates",
  description: `Browse all ${TEMPLATES.length} marriage biodata templates — Hindu, Muslim, Sikh, Christian, Jain, Buddhist and modern designs. Pick one and download a free print-ready PDF.`,
  alternates: { canonical: "/templates" },
  openGraph: { url: "/templates", title: `All Marriage Biodata Templates | ${SITE_NAME}` },
};

const shell = "mx-auto w-full max-w-[1400px] px-3 sm:px-6 lg:px-10";

export default function TemplatesPage() {
  return (
    <div className="w-full min-w-0 overflow-x-hidden bg-[#faf8f5]">
      <Header />
      <main id="main-content" className="w-full bg-gradient-to-b from-[#faf6eb] via-[#f0ebe3]/50 to-white py-12 sm:py-16">
        <div className={shell}>
          <div className="mx-auto max-w-2xl text-center">
            <p className="text-xs font-bold uppercase tracking-[0.2em] text-[#7a5c14]">Templates</p>
            <h1 className="mt-2 text-3xl font-bold tracking-tight text-[#1c1917] sm:text-4xl">
              All Marriage Biodata Templates
            </h1>
            <p className="mt-3 text-sm text-[#78716c] sm:text-base">
              {TEMPLATES.length} designs in one place. Tap any template — it opens the form with that exact design
              selected, and you can still change it later.
            </p>
          </div>
          <TemplateGallery target="/#create" paginate={false} />
        </div>
      </main>
      <footer className="w-full border-t border-[#e7e5e4] bg-[#1c1917] py-8 text-center text-xs text-white/70">
        <a href="/" className="font-semibold text-[#c4a35a] hover:underline">
          ← Back to biodata maker
        </a>
      </footer>
    </div>
  );
}
