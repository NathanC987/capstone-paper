# Appendix – I: Project Evidence and Supporting Documents {-}

This appendix collects the evidence that the department asks to be attached: publication and intellectual property records, competition certificates, the progress review sheets, supporting material and the video presentation. Items that are issued or signed by others are inserted as scans in the places marked below.

## A. IPR / Research Publication Evidence {-}

The method and results of this project are described in a research paper written by the project team:

R. Guhagarkar, N. Cherian, A. Pal, A. Patre and S. Mirchandani, "Drift Detection, Diagnosis and Reliability Analysis for Deployed Machine Learning Models," [[venue, submission date and status: submitted / accepted / presented]].

- Research paper submitted, accepted or presented, with full citation and status evidence: [[insert the submission or acceptance record]].
- Certificate of publication or presentation: [[insert if issued; otherwise write "Not yet issued"]].
- Patent or other IPR filing: no patent has been filed for this project. The patent search of Section @sec:patents found no granted or published patent that claims its drift type diagnosis.

## B. Project Competition / Award Certificates {-}

[[Attach certificates for project competitions or awards, if any. If not applicable, write "Not applicable."]]

## C. Progress Review Sheets {-}

[[Attach Progress Review Sheet 1 and Progress Review Sheet 2 in the prescribed format.]]

## D. Additional Supporting Material {-}

**Plagiarism and AI-content detection reports.** [[Attach the plagiarism report and the AI-content detection report generated on the final text of this report.]]

**Automated test run.** The test suite was run on 30 October 2026 with pytest 9.0.2 under Python 3.14.8: \res{bb-tests-total} tests passed in \res{bb-tests-seconds} seconds (\res{bb-tests-unit} unit, \res{bb-tests-integration} integration and \res{bb-tests-smoke} smoke tests), with no failures. The full log is kept with the project files (evidence/pytest-2026-10-30.txt).

**How to run the system.** From the root of the code repository, with Python 3.14 and the dependencies of pyproject.toml installed:

```Commands to reproduce the studies and open the dashboard {#alg:run}
python examples/quickstart/folktables_demo.py --task income --model lr
python examples/quickstart/gas_drift_study.py --model lr
python examples/quickstart/clear10_drift_study.py --model lr
python examples/quickstart/drift_injection_benchmark.py --dataset acs_income --design A --model lr
python examples/quickstart/remediation_demo.py --model lr
python examples/quickstart/benchmark_summary.py
python examples/paper/build_artifacts.py
streamlit run examples/dashboard/app.py --server.address 127.0.0.1
```

\noindent Each study writes its report to the outputs folder; the build script regenerates the result values, tables and figures; the last command opens the dashboard of Section @sec:ui in a browser on the local machine. Algorithm @alg:run lists the commands for one model; the other model family is run with `--model hgb`.

## E. Video Presentation {-}

[[Insert the video presentation folder link shared by the department and check that it opens for authorized reviewers.]]
