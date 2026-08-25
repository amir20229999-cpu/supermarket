
function filterProducts(){
 const q=(document.querySelector('#productSearch')?.value||'').trim().toLowerCase();
 document.querySelectorAll('[data-product]').forEach(x=>x.style.display=x.innerText.toLowerCase().includes(q)?'':'none');
}
function confirmDelete(message){return confirm(message||'حذف شود؟')}
