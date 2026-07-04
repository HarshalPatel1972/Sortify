import { useParams, Link } from "react-router-dom";
import { Download, CheckCircle, Home } from "lucide-react";

export default function DownloadPage() {
  const { jobId } = useParams();

  const handleDownload = () => {
    window.open(`http://localhost:8000/api/jobs/${jobId}/download`, "_blank");
  };

  return (
    <div className="max-w-2xl mx-auto mt-16 animate-in zoom-in-95 duration-500">
      <div className="bg-slate-800 rounded-3xl p-10 border border-white/10 shadow-2xl text-center space-y-8">
        
        <div className="mx-auto w-24 h-24 bg-green-500/20 rounded-full flex items-center justify-center">
          <CheckCircle className="w-12 h-12 text-green-400" />
        </div>
        
        <div className="space-y-4">
          <h2 className="text-3xl font-bold text-white">All Done!</h2>
          <p className="text-slate-400 text-lg">
            Your question banks have been successfully sorted, deduplicated, and grouped by topic.
          </p>
        </div>

        <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
          <button 
            onClick={handleDownload}
            className="w-full sm:w-auto bg-gradient-to-r from-indigo-500 to-cyan-500 hover:from-indigo-600 hover:to-cyan-600 text-white font-bold py-4 px-8 rounded-xl shadow-lg shadow-indigo-500/25 transition-all active:scale-[0.98] flex items-center justify-center gap-2"
          >
            <Download className="w-5 h-5" />
            Download ZIP
          </button>
          
          <Link 
            to="/"
            className="w-full sm:w-auto bg-slate-700 hover:bg-slate-600 text-white font-bold py-4 px-8 rounded-xl transition-all active:scale-[0.98] flex items-center justify-center gap-2"
          >
            <Home className="w-5 h-5" />
            Start New Job
          </Link>
        </div>
      </div>
    </div>
  );
}
