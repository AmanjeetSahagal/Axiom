import Image from "next/image";

type LogoMarkProps = {
  size?: "sm" | "md" | "lg";
};

const sizeClasses = {
  sm: {
    frame: "h-16 w-16 rounded-[20px]",
    image: "h-[5.5rem] w-[5.5rem]",
  },
  md: {
    frame: "h-24 w-24 rounded-[28px]",
    image: "h-[11rem] w-[11rem]",
  },
  lg: {
    frame: "h-28 w-28 rounded-[32px]",
    image: "h-[13rem] w-[13rem]",
  },
};

export function LogoMark({ size = "md" }: LogoMarkProps) {
  const classes = sizeClasses[size];

  return (
    <div className={`flex items-center justify-center border border-ember/20 bg-ember shadow-panel ${classes.frame}`}>
      <Image
        src="/axiom-logo-mark.png"
        alt="Axiom logo"
        width={112}
        height={112}
        className={`object-contain ${classes.image}`}
        priority
      />
    </div>
  );
}
