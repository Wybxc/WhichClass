import htmx from "htmx.org";
import { themeChange } from "theme-change";
import {
  createIcons,
  Check,
  ChevronDown,
  CalendarDays,
  Users,
  School,
  Info,
  MapPin,
  Book,
} from "lucide";

if (localStorage.getItem("theme") == null) {
  if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
    localStorage.setItem("theme", "dark");
  } else {
    localStorage.setItem("theme", "light");
  }
}
document.documentElement.setAttribute(
  "data-theme",
  localStorage.getItem("theme"),
);
themeChange();

htmx.on("htmx:load", () => {
  createIcons({
    icons: {
      Check,
      ChevronDown,
      CalendarDays,
      Users,
      School,
      Info,
      MapPin,
      Book,
    },
  });
});
