import { useTranslation } from "react-i18next";
import { NavLink } from "react-router";

import { PAGES } from "@/pages";
import { usePendingDrafts } from "@/pages/inbox/useDrafts";
import { cn } from "@/lib/utils";

export function Nav() {
  const { t } = useTranslation();
  const pending = usePendingDrafts().data?.length ?? 0;
  return (
    <nav className="flex gap-1">
      {PAGES.map((page) => (
        <NavLink
          key={page.key}
          to={page.path}
          end
          className={({ isActive }) =>
            cn("rounded-md px-3 py-2 text-sm", isActive ? "bg-neutral-900 text-white" : "hover:bg-neutral-100")
          }
        >
          {t(`nav.${page.key}`)}
          {page.key === "inbox" && pending > 0 && (
            <span
              className="ml-1.5 rounded-full bg-amber-500 px-1.5 text-xs text-white"
              title={t("inbox.pendingCount", { count: pending })}
            >
              {pending}
            </span>
          )}
        </NavLink>
      ))}
    </nav>
  );
}
