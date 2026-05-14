import type { ComponentPropsWithoutRef } from "react";
import { cn } from "@/lib/utils";

export function Card({ className, ...props }: ComponentPropsWithoutRef<"section">) {
  return (
    <section
      className={cn("glass-surface min-w-0 rounded-2xl p-5 motion-safe", className)}
      {...props}
    />
  );
}
