import "./App.css";
import { BrowserRouter, Route, Routes } from "react-router-dom";
import { Home } from "./pages/Home.jsx";
import { Menu } from "./pages/Menu.jsx";


function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/menu-plan" element={<Menu />} />
      </Routes>
      
    </BrowserRouter>
  );
}

export default App;