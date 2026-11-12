import Spinner from "../ui/Spinner";

export default function LoadingState({ label = "Loading..." }) {
  return (
    <div className="flex items-center justify-center gap-3 p-10 text-slate-500">
      <Spinner /> {label}
    </div>
  );
}
