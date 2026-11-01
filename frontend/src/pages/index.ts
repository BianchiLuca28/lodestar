import type { ComponentType } from "react";

import { ChatPage } from "./chat/ChatPage";
import { InboxPage } from "./inbox/InboxPage";
import { MovimentiPage } from "./movimenti/MovimentiPage";
import { PanoramicaPage } from "./panoramica/PanoramicaPage";
import { PianoPage } from "./piano/PianoPage";
import { PortafoglioPage } from "./portafoglio/PortafoglioPage";

/** The six pages of the app (ADR 0014). New features become sections of one of these. */
export const PAGES: { key: string; path: string; Component: ComponentType }[] = [
  { key: "panoramica", path: "/", Component: PanoramicaPage },
  { key: "inbox", path: "/inbox", Component: InboxPage },
  { key: "movimenti", path: "/movimenti", Component: MovimentiPage },
  { key: "portafoglio", path: "/portafoglio", Component: PortafoglioPage },
  { key: "piano", path: "/piano", Component: PianoPage },
  { key: "chat", path: "/chat", Component: ChatPage },
];
