import { BrowserRouter, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import Budget from './pages/Budget';
import Import from './pages/Import';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<Layout />}>
          <Route path="/" element={<Budget />} />
          <Route path="/import" element={<Import />} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
