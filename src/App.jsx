import React from 'react';
import {BrowserRouter,Routes,Route,Navigate} from 'react-router-dom';
import Provider from './context/AuthContext';
import RegistrationAcceptanceSync from './components/RegistrationAcceptanceSync';
import PublicProfile from './pages/PublicProfile';
import Layout from './components/Layout.jsx';
import Protected from './components/Protected.jsx';
import VideoGrid from './components/VideoGrid.jsx';
import Home from './pages/Home.jsx';
import Videos from './pages/Videos.jsx';
import VideoPage from './pages/VideoPage.jsx';
import Auth from './pages/Auth.jsx';
import UploadPage from './pages/Upload.jsx';
import Profile from './pages/Profile.jsx';
import Admin from './pages/Admin.jsx';
import Messages from './pages/Messages.jsx';
import About from './pages/About.jsx';
function App(){return <Provider><BrowserRouter><Layout><Routes><Route path="/" element={<Home/>}/><Route path="/videos" element={<Videos/>}/><Route path="/video/:id" element={<VideoPage/>}/><Route path="/farmer/:username" element={<PublicProfile/>}/><Route path="/auth" element={<Auth/>}/><Route path="/upload" element={<Protected><UploadPage/></Protected>}/><Route path="/profile" element={<Protected><Profile/></Protected>}/><Route path="/messages" element={<Protected><Messages/></Protected>}/><Route path="/admin" element={<Protected admin><Admin/></Protected>}/><Route path="/about" element={<About/>}/><Route path="*" element={<Navigate to="/"/>}/></Routes><RegistrationAcceptanceSync/></Layout></BrowserRouter></Provider>}

export default App;
