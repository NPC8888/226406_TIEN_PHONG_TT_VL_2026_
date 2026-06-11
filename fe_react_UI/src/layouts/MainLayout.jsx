import { Outlet } from "react-router-dom";
import Navbar from "@/components/Navbar/NavbarGoogle";

function MainLayout() {
  return (
    <>
      <Navbar />
      <Outlet />
    </>
  );
}

export default MainLayout;
