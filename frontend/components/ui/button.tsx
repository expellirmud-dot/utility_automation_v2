import type { ButtonHTMLAttributes } from "react";
import { cn } from "@/lib/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "soft" | "ghost";
};

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex min-h-10 items-center justify-center gap-2 whitespace-nowrap rounded-2xl px-4 text-sm font-semibold motion-safe focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#0f7c86]",
        variant === "primary" &&
          "bg-[#0f7c86] text-white shadow-[0_12px_28px_rgba(15,124,134,0.22)] hover:bg-[#0c6871]",
        variant === "soft" &&
          "border border-[#c7e8ea] bg-[#e5f6f7] text-[#0d6972] hover:bg-[#d4eff1]",
        variant === "ghost" &&
          "text-slate-600 hover:bg-white/72 hover:text-slate-950",
        className,
      )}
      {...props}
    />
  );
}
