import { useTranslation } from "react-i18next";

export function PagePlaceholder({ titleKey }: { titleKey: string }) {
  const { t } = useTranslation();
  return (
    <section>
      <h1 className="text-2xl font-semibold">{t(titleKey)}</h1>
      <p className="mt-2 text-neutral-500">{t("page.placeholder")}</p>
    </section>
  );
}
