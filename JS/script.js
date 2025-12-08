function getComputerChoice() {
    const choices = ["rock", "paper", "scissors"];
    return choices[Math.floor(Math.random() * choices.length)];
}

function playRound(playerSelection, computerSelection) {
    if (playerSelection === computerSelection) return "It's a tie!";
    if (
        (playerSelection === "rock" && computerSelection === "scissors") ||
        (playerSelection === "paper" && computerSelection === "rock") ||
        (playerSelection === "scissors" && computerSelection === "paper")
    ) return "You win!";
    return "Computer wins!";
}

function playGame() {
    let playerScore = 0;
    let computerScore = 0;

    for (let round = 1; round <= 5; round++) {
        let playerChoice = prompt(`Round ${round}: Rock, Paper, or Scissors?`).toLowerCase();
        let computerChoice = getComputerChoice();
        let result = playRound(playerChoice, computerChoice);

        if (result === "You win!") playerScore++;
        if (result === "Computer wins!") computerScore++;

        alert(`Round ${round}:\nYou chose ${playerChoice}\nComputer chose ${computerChoice}\n${result}`);
    }

    alert(`Final Score:\nYou: ${playerScore} | Computer: ${computerScore}`);
}

playGame();
