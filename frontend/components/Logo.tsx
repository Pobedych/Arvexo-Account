import Image from "next/image";
import Link from "next/link";

export function Logo({ compact = false }: { compact?: boolean }) {
  return (
    <Link href="/" className={compact ? "site-logo site-logo-compact" : "site-logo"} aria-label="Arvexo Account">
      <Image src="/images/arvexo-mark.png" alt="" aria-hidden="true" className="site-logo-mark" width={495} height={480} priority />
      {!compact && (
        <Image
          src="/images/arvexo-wordmark.png"
          alt=""
          aria-hidden="true"
          className="site-logo-wordmark"
          width={728}
          height={121}
          priority
        />
      )}
    </Link>
  );
}
