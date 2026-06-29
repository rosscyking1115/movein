import Link from "next/link";
import { Logo } from "./Logo";
import { NavLinks } from "./NavLinks";
import { ThemeToggle } from "./ThemeToggle";

export function SiteHeader() {
  return (
    <header className="sticky top-0 z-20 border-b border-rule bg-paper">
      <div className="mx-auto flex h-[62px] max-w-[1140px] items-center gap-7 px-6">
        <Link href="/" aria-label="MoveIn home" className="flex items-center gap-2.5">
          <Logo size={26} />
          <span className="font-display text-[25px] font-bold leading-none text-ink">MoveIn</span>
        </Link>
        <NavLinks />
        <ThemeToggle />
      </div>
    </header>
  );
}
