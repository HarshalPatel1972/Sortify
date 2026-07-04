import { BrowserRouter, Routes, Route } from "react-router-dom";
import UploadPage from "./pages/UploadPage";
import ProgressPage from "./pages/ProgressPage";
import ReviewPage from "./pages/ReviewPage";
import DownloadPage from "./pages/DownloadPage";
import Layout from "./components/Layout";

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<UploadPage />} />
          <Route path="job/:jobId/progress" element={<ProgressPage />} />
          <Route path="job/:jobId/review" element={<ReviewPage />} />
          <Route path="job/:jobId/download" element={<DownloadPage />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}

export default App;
