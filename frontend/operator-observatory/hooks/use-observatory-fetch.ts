import { useState, useEffect } from "react";

type LoadState<T> =
  | { status: "loading" }
  | { status: "ready"; data: T }
  | { status: "empty" }
  | { status: "degraded"; message: string }
  | { status: "error"; message: string };

export function useObservatoryFetch<T>(
  fetchFn: () => Promise<T>,
  emptyCheck?: (data: T) => boolean,
  degradedCheck?: (data: T) => string | null,
): LoadState<T> {
  const [state, setState] = useState<LoadState<T>>({ status: "loading" });

  useEffect(() => {
    let active = true;

    fetchFn()
      .then((data) => {
        if (!active) return;

        if (emptyCheck && emptyCheck(data)) {
          setState({ status: "empty" });
          return;
        }

        if (degradedCheck) {
          const degradation = degradedCheck(data);
          if (degradation) {
            setState({ status: "degraded", message: degradation });
            return;
          }
        }

        setState({ status: "ready", data });
      })
      .catch((error: unknown) => {
        if (active) {
          setState({
            status: "error",
            message: error instanceof Error ? error.message : "Unable to read observability data.",
          });
        }
      });

    return () => {
      active = false;
    };
  }, [fetchFn]);

  return state;
}
