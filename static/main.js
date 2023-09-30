document.addEventListener('DOMContentLoaded', () => {
    document.querySelector('#search').addEventListener('keyup', filter_table);
});

function filter_table() {
    let filter = document.querySelector('#search').value.toUpperCase();
    let table = document.querySelector('#tableBody');
    let rows = table.querySelectorAll('tr');
    for (let i = 0; i < rows.length; i++) {
        let td = rows[i].getElementsByTagName('td')[1];
        if (td) {
            let txtValue = td.textContent || td.innerText;
            if (txtValue.toUpperCase().indexOf(filter) > -1) {
                rows[i].style.display = '';
            } else {
                rows[i].style.display = 'none';
            }
        }
    }
}
