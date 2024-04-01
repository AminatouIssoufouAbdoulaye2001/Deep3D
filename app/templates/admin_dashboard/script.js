const sidebar = document.querySelector(".sidebar");
const sidebarBtn = document.querySelector(".sidebarBtn");


sidebarBtn.onclick = ()=>{
    sidebar.classList.toggle("active");
}