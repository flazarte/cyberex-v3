const START = new Date(init.start * 1000);
const END = new Date(init.end * 1000);

// const disp_phase = document.getElementById("countdown-phase");
const countdown_disp = document.getElementById("countdown");

const disp = {
    hour: countdown_disp.querySelector(".hour"),
    minute: countdown_disp.querySelector(".minute"),
    second: countdown_disp.querySelector(".second"),
}

let countdown_interval_id = null;


//multiplayers
const countdown_multiplayer = () => {
    const NOW = new Date();
    let compareTo;
    
    if (NOW > END) {
	// We done! Ty for participating!
	// disp_phase.textContent = "CTK is over! Thanks for participating!";
	compareTo = null;
	countdown_disp.remove();
	clearInterval(countdown_interval_id);
	return;
    } else if (NOW > START) {
	// We started boisss
	// disp_phase.textContent = "Ending in...";
	compareTo = END;
    } else {
	// Still waiting for it to start! Hypeee!!1!
	// disp_phase.textContent = "Starting in...";
	compareTo = START;
    }

    const diff = Math.floor((compareTo - NOW) / 1000);
    disp.hour.textContent = (Math.floor(diff / 3600)).toString().padStart(2, "0");
    disp.minute.textContent = (Math.floor(diff / 60) % 60).toString().padStart(2, "0");
    disp.second.textContent = (diff % 60).toString().padStart(2, "0");
};

//individuals

// const disp_phase_users = document.getElementById("countdown-phase-users");
// const countdown_disp_users = document.getElementById("countdown-users");

// const disp_users = {
//     hour: countdown_disp_users.querySelector(".hour"),
//     minute: countdown_disp_users.querySelector(".minute"),
//     second: countdown_disp_users.querySelector(".second"),
// }

// let countdown_interval_user_id = null;

// const countdown_individuals = () => {
//     const NOW = new Date();
//     let compareTo;
    
//     if (NOW > END) {
// 	// We done! Ty for participating!
// 	disp_phase_users.textContent = "CTK is over! Thanks for participating!";
// 	compareTo = null;
// 	countdown_disp_users.remove();
// 	clearInterval(countdown_interval_user_id);
// 	return;
//     } else if (NOW > START) {
// 	// We started boisss
// 	disp_phase_users.textContent = "Ending in...";
// 	compareTo = END;
//     } else {
// 	// Still waiting for it to start! Hypeee!!1!
// 	disp_phase_users.textContent = "Starting in...";
// 	compareTo = START;
//     }

//     const diff = Math.floor((compareTo - NOW) / 1000);
//     disp_users.hour.textContent = (Math.floor(diff / 3600)).toString().padStart(2, "0");
//     disp_users.minute.textContent = (Math.floor(diff / 60) % 60).toString().padStart(2, "0");
//     disp_users.second.textContent = (diff % 60).toString().padStart(2, "0");
// };

countdown_multiplayer();
//countdown_individuals();
countdown_interval_id = setInterval(countdown_multiplayer, 1000);
//countdown_interval_user_id = setInterval(countdown_individuals, 1000);


/////////////////////Directorate Dashboard//////////
const ctk_time = document.getElementById("ctk-time");
const time = {
    start: ctk_time.querySelector(".start"),
    end: ctk_time.querySelector(".end"),
}
time.start.textContent = START.toDateString();
time.end.textContent = END.toDateString();

