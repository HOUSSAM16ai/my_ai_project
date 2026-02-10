import { useEffect, useRef, useState, useCallback } from "react";

const MAX_BACKOFF = 10000;

/**
 * Hook to manage a robust WebSocket connection.
 * @param {string} wsUrl - The WebSocket URL.
 * @param {string} token - The authentication token.
 * @returns {{ state: string, sendMessage: (data: any) => void }}
 */
export function useRealtimeConnection(wsUrl, token) {
  const wsRef = useRef(null);
  const retries = useRef(0);
  const [state, setState] = useState("idle");
  const mountedRef = useRef(true);
  const reconnectTimeoutRef = useRef(null);

  const connect = useCallback(() => {
    if (!wsUrl || !token) return;
    if (wsRef.current && (wsRef.current.readyState === WebSocket.OPEN || wsRef.current.readyState === WebSocket.CONNECTING)) return;

    setState("connecting");

    try {
        const ws = new WebSocket(wsUrl, ["jwt", token]);
        wsRef.current = ws;

        ws.onopen = () => {
          if (mountedRef.current) {
            retries.current = 0;
            setState("connected");
          }
        };

        ws.onmessage = (event) => {
          if (!mountedRef.current) return;
          try {
            const data = JSON.parse(event.data);
            // Broadcast agent events
            window.dispatchEvent(
              new CustomEvent("agent:event", {
                detail: data,
              })
            );
          } catch (e) {
            console.error("Failed to parse WebSocket message:", e);
          }
        };

        ws.onerror = (e) => {
          if (mountedRef.current) {
              setState("degraded");
          }
          console.error("WebSocket error:", e);
        };

        ws.onclose = (e) => {
          if (mountedRef.current) {
             wsRef.current = null;
             setState("offline");

             // Clean close or auth error: don't reconnect immediately?
             // User's code reconnects on close. I will follow that but with backoff.
             // "No hysterical reconnect" is solved by backoff.

             const delay = Math.min(
               2 ** retries.current * 500,
               MAX_BACKOFF
             );

             retries.current += 1;
             clearTimeout(reconnectTimeoutRef.current);
             reconnectTimeoutRef.current = setTimeout(connect, delay);
          }
        };
    } catch (err) {
        console.error("WebSocket connection failed:", err);
        if (mountedRef.current) setState("offline");
        // Retry?
        const delay = Math.min(
            2 ** retries.current * 500,
            MAX_BACKOFF
        );
        retries.current += 1;
        clearTimeout(reconnectTimeoutRef.current);
        reconnectTimeoutRef.current = setTimeout(connect, delay);
    }
  }, [wsUrl, token]);

  const sendMessage = useCallback((data) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify(data));
    } else {
      console.warn("WebSocket is not connected. Message dropped.", data);
    }
  }, []);

  useEffect(() => {
    mountedRef.current = true;
    connect();
    return () => {
      mountedRef.current = false;
      if (wsRef.current) wsRef.current.close();
      clearTimeout(reconnectTimeoutRef.current);
    };
  }, [connect]);

  return { state, sendMessage };
}
