// Optional: basic calculator modal
function calculateTotal() {
  const amount = parseFloat(document.querySelector("input[name='amount']").value);
  const quantity = parseFloat(prompt("Enter quantity:"));
  if (!isNaN(amount) && !isNaN(quantity)) {
    alert("Total = " + (amount * quantity).toFixed(2));
  } else {
    alert("Please enter valid numbers.");
  }
}