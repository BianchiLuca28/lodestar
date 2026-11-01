import { useTranslation } from "react-i18next";
import { NavLink } from "react-router";

import { PAGES } from "@/pages";
import { cn } from "@/lib/utils";

export function Nav() {
  const { t } = useTranslation();
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
        </NavLink>
      ))}
    </nav>
  );
}
