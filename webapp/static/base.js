function postfn() {
  document.getElementById("reply").innerHTML = "working";
  let license_plate = document.getElementById("license_plate").value;
  let email = document.getElementById("email").value;
  let confirmation = document.getElementById("confirmation").checked;
  console.log(`license_plate: ${license_plate}`);
  const xhr = new XMLHttpRequest();
  xhr.open("POST", "/register");
  xhr.setRequestHeader("Content-Type", "application/json; charset=UTF-8");
  const body = JSON.stringify({
    license_plate: license_plate,
    email: email,
    confirmation: confirmation,
  });
  console.log(body);
  xhr.send(body);
  xhr.onload = () => {
    if (xhr.readyState === xhr.DONE) {
      if (xhr.status === 200) {
        console.log(xhr.response);
        console.log(xhr.responseText);
        let response = xhr.response;
        document.getElementById("reply").innerHTML = response;
      }
    }
  };
}
