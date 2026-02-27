import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { AuthProvider } from './lib/useAuth'
import Nav from './components/Nav'
import Meta from './pages/Meta'
import TeamRadar from './pages/TeamRadar'
import MyRecord from './pages/MyRecord'
import Account from './pages/Account'

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Nav />
        <Routes>
          <Route path="/"        element={<Meta />} />
          <Route path="/radar"   element={<TeamRadar />} />
          <Route path="/record"  element={<MyRecord />} />
          <Route path="/account" element={<Account />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
