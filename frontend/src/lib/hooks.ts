import { useCallback, useEffect, useState } from "react";
import { ApiError } from "../api";

export function messageOf(error: unknown): string {
  return error instanceof ApiError ? error.message : "Something unexpected went wrong.";
}

/** Load data when the component mounts or `key` changes; expose a manual reload. */
export function useLoad<T>(load: () => Promise<T>, key: unknown = null) {
  const [data, setData] = useState<T | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [tick, setTick] = useState(0);

  useEffect(() => {
    let current = true;
    setError(null);
    load().then(
      (value) => current && setData(value),
      (reason) => current && setError(messageOf(reason)),
    );
    return () => {
      current = false;
    };
    // `load` is recreated every render; `key` and `tick` say when to actually reload.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key, tick]);

  const reload = useCallback(() => setTick((n) => n + 1), []);
  return { data, error, reload, setData };
}

/** The part of the URL after `#`, so views are linkable and the back button works. */
export function useHashRoute(): string {
  const read = () => window.location.hash.replace(/^#\/?/, "") || "search";
  const [route, setRoute] = useState(read);
  useEffect(() => {
    const onChange = () => setRoute(read());
    window.addEventListener("hashchange", onChange);
    return () => window.removeEventListener("hashchange", onChange);
  }, []);
  return route;
}
