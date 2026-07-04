import { useState, useEffect } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { Edit2, Check, ArrowRight } from "lucide-react";

export default function ReviewPage() {
  const { jobId } = useParams();
  const navigate = useNavigate();
  const [clusters, setClusters] = useState([]);
  const [editingId, setEditingId] = useState(null);
  const [editValue, setEditValue] = useState("");
  const [isFinalizing, setIsFinalizing] = useState(false);

  useEffect(() => {
    const fetchClusters = async () => {
      const res = await fetch(`http://localhost:8000/api/jobs/${jobId}/clusters`);
      const data = await res.json();
      setClusters(data);
    };
    fetchClusters();
  }, [jobId]);

  const saveTopic = async (clusterId) => {
    await fetch(`http://localhost:8000/api/jobs/${jobId}/clusters/${clusterId}?topic_label=${encodeURIComponent(editValue)}`, {
      method: "PATCH"
    });
    setClusters(clusters.map(c => c.id === clusterId ? { ...c, topic_label: editValue } : c));
    setEditingId(null);
  };

  const handleFinalize = async () => {
    setIsFinalizing(true);
    await fetch(`http://localhost:8000/api/jobs/${jobId}/finalize`, { method: "POST" });
    setIsFinalizing(false);
    navigate(`/job/${jobId}/download`);
  };

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold">Review Topics</h1>
          <p className="text-slate-400 mt-1">We've grouped similar questions. Review and edit the AI-generated topics.</p>
        </div>
        <button
          onClick={handleFinalize}
          disabled={isFinalizing}
          className="bg-indigo-500 hover:bg-indigo-600 text-white px-6 py-3 rounded-xl font-semibold flex items-center gap-2 transition-all shadow-lg shadow-indigo-500/20 active:scale-95"
        >
          {isFinalizing ? "Generating PDFs..." : "Looks Good, Finalize"}
          {!isFinalizing && <ArrowRight className="w-5 h-5" />}
        </button>
      </div>

      <div className="space-y-6">
        {clusters.map(cluster => (
          <div key={cluster.id} className="bg-slate-800 border border-white/10 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6 border-b border-white/10 pb-4">
              <div className="flex items-center gap-4">
                {editingId === cluster.id ? (
                  <div className="flex items-center gap-2">
                    <input
                      type="text"
                      className="bg-slate-900 border border-indigo-500 rounded-lg px-4 py-2 text-white outline-none w-64"
                      value={editValue}
                      onChange={(e) => setEditValue(e.target.value)}
                      onKeyDown={(e) => e.key === 'Enter' && saveTopic(cluster.id)}
                      autoFocus
                    />
                    <button onClick={() => saveTopic(cluster.id)} className="p-2 bg-indigo-500 rounded-lg hover:bg-indigo-600 transition-colors">
                      <Check className="w-5 h-5" />
                    </button>
                  </div>
                ) : (
                  <div className="flex items-center gap-3">
                    <h2 className="text-2xl font-semibold text-white">
                      {cluster.topic_label || "Uncategorized"}
                    </h2>
                    <button 
                      onClick={() => {
                        setEditingId(cluster.id);
                        setEditValue(cluster.topic_label || "");
                      }}
                      className="p-1.5 text-slate-400 hover:text-white hover:bg-white/10 rounded-md transition-colors"
                    >
                      <Edit2 className="w-4 h-4" />
                    </button>
                  </div>
                )}
              </div>
              <div className="bg-slate-700 px-3 py-1 rounded-full text-sm font-medium text-slate-300">
                {cluster.questions.length} questions
              </div>
            </div>

            <div className="flex gap-4 overflow-x-auto pb-4 custom-scrollbar">
              {cluster.questions.slice(0, 5).map(q => (
                <div key={q.id} className="min-w-[300px] max-w-[300px] bg-slate-900 rounded-xl overflow-hidden border border-white/5">
                  <div className="h-40 overflow-hidden flex items-center justify-center bg-white p-2">
                    <img 
                      src={`http://localhost:8000/api/images/${encodeURIComponent(q.crop_image_path.split('\\').pop() || q.crop_image_path.split('/').pop())}`} 
                      alt="Question snippet" 
                      className="max-w-full max-h-full object-contain"
                      onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'block'; }}
                    />
                    <div style={{display: 'none'}} className="text-slate-800 text-xs p-4">{q.extracted_text.substring(0, 150)}...</div>
                  </div>
                </div>
              ))}
              {cluster.questions.length > 5 && (
                <div className="min-w-[150px] flex items-center justify-center bg-slate-800/50 rounded-xl border border-dashed border-white/20">
                  <span className="text-slate-400 font-medium">+{cluster.questions.length - 5} more</span>
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
