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
} from "lucide";

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
    },
  });
});
