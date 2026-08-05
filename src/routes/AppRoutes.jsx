import { BrowserRouter, Routes, Route } from "react-router-dom";
import Login from "../pages/Login";
import Dashboard from "../pages/Dashboard";
import Upload from "../pages/Upload";
import Workspace from "../pages/Workspace";
import UploadHistory from "../pages/UploadHistory";
import Sessions from "../pages/Sessions";

function AppRoutes(){
    return(
        <BrowserRouter>
        <Routes>
            <Route path="/" element={<Login/>}/>
            <Route path="/dashboard" element={<Dashboard/>}/>
            <Route path="/upload" element={<Upload/>}/>
            <Route path="/workspace" element={<Workspace/>}/>
            <Route path="/history" element={<UploadHistory/>}/>
            <Route path="/sessions" element={<Sessions/>}/>
        </Routes>
        </BrowserRouter>
    );
}
export default AppRoutes;