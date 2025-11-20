

document.addEventListener("DOMContentLoaded", () => {
  // ----- Section switching (the 3 big buttons) -----
  const actionButtons = document.querySelectorAll(".action-btn");
  const sections = {
    report: document.getElementById("section-report"),
    recent: document.getElementById("section-recent"),
    predict: document.getElementById("section-predict"),
  };

  actionButtons.forEach((btn) => {
    btn.addEventListener("click", () => {
      const target = btn.getAttribute("data-section");

      // Toggle button styles
      actionButtons.forEach(b => b.classList.remove("active"));
      btn.classList.add("active");

      // Toggle visible card
      Object.entries(sections).forEach(([key, sectionEl]) => {
        if (key === target) {
          sectionEl.classList.add("active");
        } else {
          sectionEl.classList.remove("active");
        }
      });
    });
  });

  // ----- Report form -----
  const formReport = document.getElementById("form-report");
  const submitStatus = document.getElementById("submit-status");

  formReport.addEventListener("submit", async (event) => {
    event.preventDefault();
    submitStatus.textContent = "Submitting...";
    submitStatus.className = "status";

    const payload = {
      location_name: document.getElementById("location_name").value.trim(),
      hazard_type: document.getElementById("hazard_type").value.trim(),
      accessibility: document.getElementById("accessibility").value,
      user_type: document.getElementById("user_type").value,
      temporary: document.getElementById("temporary").checked,
      description: document.getElementById("description").value.trim()
    };

    try {
      const response = await fetch("/api/report", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      const data = await response.json();

      if (!response.ok) {
        submitStatus.textContent = "Error: " + (data.error || "Failed to submit");
        submitStatus.classList.add("error");
      } else {
        submitStatus.textContent = "Thank you! Your report has been saved and will help train the model.";
        submitStatus.classList.add("success");
        formReport.reset();
        document.getElementById("temporary").checked = true;
      }
    } catch (err) {
      submitStatus.textContent = "Network error submitting hazard.";
      submitStatus.classList.add("error");
    }
  });

  // ----- Recent hazards form -----
  const formRecent = document.getElementById("form-recent");
  const hazardResults = document.getElementById("hazard-results");

  formRecent.addEventListener("submit", async (event) => {
    event.preventDefault();
    hazardResults.textContent = "Loading recent hazards...";

    const location = document.getElementById("check-location").value.trim();
    if (!location) {
      hazardResults.textContent = "Please enter a location.";
      return;
    }

    try {
      const res = await fetch(`/api/hazards?location=${encodeURIComponent(location)}`);
      const data = await res.json();

      hazardResults.innerHTML = "";

      if (data.hazards && data.hazards.length > 0) {
        const list = document.createElement("ul");
        list.className = "results-list";

        data.hazards.forEach(h => {
          const li = document.createElement("li");
          li.innerHTML =
            `<span class="pill"><span class="dot"></span>${h.day} • ${h.timestamp}</span><br>` +
            `<strong>${h.location_name}</strong> – ${h.hazard_type} ` +
            `(accessibility: ${h.accessibility}/5, user: ${h.user_type})` +
            (h.description ? `<br><em>${h.description}</em>` : "");
          list.appendChild(li);
        });

        hazardResults.appendChild(list);
      } else {
        hazardResults.textContent = "No recent hazards for this location.";
      }
    } catch (err) {
      hazardResults.textContent = "Error fetching hazards.";
    }
  });

});
