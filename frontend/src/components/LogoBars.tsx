import { cn } from "@/lib/utils";

type LogoBarsProps = {
  className?: string;
  barClassName?: string;
};

export default function LogoBars({ className, barClassName }: LogoBarsProps) {
  return (
    <div className={cn("flex h-8 w-8 flex-col items-center justify-center gap-[3px]", className)}>
      <div className={cn("h-[5px] w-[18px] rounded-xl bg-foreground", barClassName)} />
      <div className={cn("h-[5px] w-[26px] rounded-xl bg-foreground", barClassName)} />
      <div className={cn("h-[5px] w-[18px] rounded-xl bg-foreground", barClassName)} />
    </div>
  );
}
