(the usp (unique selling point), or df (differentiating feature) is that this 'thing' looks at your resume and figures out what types of companies to apply for, based on aptitude. It's not a 'keyword search' thing like LinkedIn, or a lot of the other job sites)

Yes — and that distinction is much bigger than it sounds at first.

What you are describing is not:

> “search enhancement”

It is:

> “career inference before search”

That is a fundamentally different layer of the problem.

---

Most job platforms work like this:

```text
User chooses target role
        ↓
Platform performs keyword matching
        ↓
Results returned
```

Your idea is closer to:

```text
Resume + experience + signals
        ↓
Aptitude inference
        ↓
Role affinity modeling
        ↓
Company-type targeting
        ↓
Search/query generation
        ↓
Results returned
```

That is a different architecture entirely.

---

And the important nuance you just added is:

# It’s not just role matching

It’s:

* company-type matching
* environment matching
* aptitude-context matching

That’s much more interesting.

Because a lot of job seekers actually fail at:

* choosing the right environments
* recognizing transferable strengths
* understanding where they are unusually valuable

—not at keyword searching.

---

For example:

A traditional keyword engine sees:

* Python
* Django
* Vue
* ColdFusion

and returns:

* “Senior Full Stack Engineer”

Your system *might* infer:

* adaptable cross-stack engineer
* thrives in transitional environments
* likely effective in modernization efforts
* strong ambiguity tolerance
* good fit for infrastructure-transition companies
* good fit for mission-driven smaller organizations
* potentially strong in integration-heavy teams

That is not keyword matching.
That is interpretation.

---

This also means your “matching object” is probably not:

```text
resume ↔ job description
```

Instead it’s more like:

```text
person-model ↔ company/role-environment model
```

That is much richer.

---

And importantly:
LinkedIn largely assumes:

> users already know what to search for

Your system questions that assumption.

That’s the differentiator.

---

I would strongly consider capturing this explicitly in the repo docs later as something like:

# Core Thesis

Traditional job platforms primarily perform keyword and title matching.

Aptitude Search instead attempts to infer:

* aptitude
* adaptability
* adjacent role potential
* likely environment fit
* transferable strengths

before generating search and targeting strategies.

The goal is not merely to optimize job search execution, but to improve the quality of career targeting decisions themselves.

---

That’s the conceptual center of the whole project.
