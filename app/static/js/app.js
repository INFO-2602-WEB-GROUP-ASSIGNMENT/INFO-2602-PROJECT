
async function getUserData(){
    const response = await fetch('/api/users');
    return response.json();
}

function loadTable(users){
    const table = document.querySelector('#result');
    for(let user of users){
        table.innerHTML += `<tr>
            <td>${user.id}</td>
            <td>${user.username}</td>
        </tr>`;
    }
}

async function main(){
    const users = await getUserData();
    loadTable(users);
}

async function fetchRoutine(id){
    const response = await fetch(`/api/routines/${id}`);
    return response.json(); // this object will be used to call the renderRoutine function, which will render the routine on the page. Not implemented yet, but will be in the future.
}

// this function will be used to create a new routine. It will be called when the user submits the form to create a new routine.
async function createRoutine(name, user_id, description, difficulty){
    formData = new FormData();
    formData.append('name', name);
    formData.append('user_id', user_id);
    formData.append('description', description);
    formData.append('difficulty', difficulty);

    const response = await fetch('/api/routines', {
        method: 'POST',
        body: formData
    });

    return response.json();
}


main();