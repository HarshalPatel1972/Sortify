import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Loader2, CheckCircle2, AlertCircle } from "lucide-react";

export default function ProgressPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [status, setStatus] = useState(null);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await fetch(`http://localhost:8000/api/jobs/${jobId}`);
        const data = await res.json();
        setStatus(data);

        if (data.status === "done") {
          // If done, navigate to review
          navigate(`/job/${jobId}/review`);
        }
      } catch (err) {
        console.error(err);
      }
    };

    const interval = setInterval(checkStatus, 2000);
    checkStatus();

    return () => clearInterval(interval);
  }, [jobId, navigate]);

  if (!status) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-indigo-400" />
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto mt-16 animate-in zoom-in-95 duration-500">
      <div className="bg-slate-800 rounded-3xl p-10 border border-white/10 shadow-2xl text-center space-y-8">
        
        {status.status === "error" ? (
          <>
            <div className="mx-auto w-24 h-24 bg-red-500/20 rounded-full flex items-center justify-center">
              <AlertCircle className="w-12 h-12 text-red-500" />
            </div>
            <h2 className="text-3xl font-bold text-red-400">Processing Failed</h2>
            <p className="text-slate-400">There was an error processing your job. Please try again.</p>
          </>
        ) : (
          <>
            <div className="relative mx-auto w-32 h-32">
              <svg className="w-full h-full -rotate-90" viewBox="0 0 100 100">
                <circle className="text-slate-700 stroke-current" strokeWidth="8" cx="50" cy="50" r="40" fill="transparent"></circle>
                <circle 
                  className="text-indigo-500 stroke-current transition-all duration-1000 ease-out" 
                  strokeWidth="8" 
                  strokeLinecap="round" 
                  cx="50" cy="50" r="40" fill="transparent" 
                  strokeDasharray={`${(status.processed_pdfs / (status.total_pdfs || 1)) * 251.2} 251.2`}
                ></circle>
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-2xl font-bold text-white">{status.processed_pdfs}/{status.total_pdfs}</span>
                <span className="text-xs text-slate-400 font-medium">PDFs</span>
              </div>
            </div>

            <div className="space-y-2">
              <h2 className="text-2xl font-bold text-white">Analyzing Question Banks</h2>
              <p className="text-slate-400">
                {status.status === "queued" ? "Waiting in queue..." : 
                 status.status === "processing" ? "Splitting, deduping, and clustering..." : 
                 "Finishing up..."}
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
