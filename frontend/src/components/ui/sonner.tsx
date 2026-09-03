import { useTheme } from "next-themes";
import { Toaster as Sonner, toast } from "sonner";

type ToasterProps = React.ComponentProps<typeof Sonner>;

const Toaster = ({ ...props }: ToasterProps) => {
  const { theme = "system" } = useTheme();

  return (
    <Sonner
      theme={theme as ToasterProps["theme"]}
      className="toaster group"
      toastOptions={{
        classNames: {
          toast:
            "group toast group-[.toaster]:bg-white group-[.toaster]:text-[#000] group-[.toaster]:border-black/10 group-[.toaster]:shadow-sm",
          description: "group-[.toast]:text-black/50",
          actionButton: "group-[.toast]:bg-[#000] group-[.toast]:text-white",
          cancelButton: "group-[.toast]:bg-[#F9F9F9] group-[.toast]:text-black/50",
        },
      }}
      {...props}
    />
  );
};

export { Toaster, toast };
