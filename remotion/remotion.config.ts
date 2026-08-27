import { Config } from "@remotion/cli/config";
import dns from "node:dns";

// En este equipo (Windows/Node 24) "localhost" resuelve a IPv6 primero, pero
// el Chrome headless de Remotion solo escucha en IPv4: sin esto, render()
// tira TimeoutError "trying to connect to the browser".
dns.setDefaultResultOrder("ipv4first");

Config.setVideoImageFormat("jpeg");
