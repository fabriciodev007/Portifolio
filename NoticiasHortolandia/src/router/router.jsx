import { Routes, Route, Outlet } from 'react-router';
import DefaultLayout from '../DefaultLayout.jsx';
import Home from '../page/home.jsx';

function Router() {
  return (
    <Routes>
      <Route element={<DefaultLayout />}>
        <Route path="/" element={<Home />} />
      </Route>
    </Routes>
  );
}

export default Router;