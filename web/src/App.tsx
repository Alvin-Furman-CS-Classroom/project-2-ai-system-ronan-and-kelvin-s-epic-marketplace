import { BrowserRouter, Routes, Route } from "react-router-dom";
import HomePage from "./pages/HomePage";
import SearchResultsPage from "./pages/SearchResultsPage";
import ProductDetailPage from "./pages/ProductDetailPage";
import RerankComparisonPage from "./pages/RerankComparisonPage";
import EvaluatePage from "./pages/EvaluatePage";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<HomePage />} />
        <Route path="/search" element={<SearchResultsPage />} />
        <Route path="/compare" element={<RerankComparisonPage />} />
        <Route path="/evaluate" element={<EvaluatePage />} />
        <Route path="/product/:id" element={<ProductDetailPage />} />
      </Routes>
    </BrowserRouter>
  );
}
