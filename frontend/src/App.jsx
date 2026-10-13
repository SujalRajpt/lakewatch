import { useEffect, useState } from "react";
import {
  getHealth,
  getLakes,
  getLake,
  getSensors,
  getSensor,
  getReadings,
  getLakeReadings,
  getLatestReading,
} from "./services/api";
import Navbar from "./components/Navbar";
import Dashboard from "./pages/Dashboard";
import Lakes from "./pages/Lakes";
import LakeDetails from "./pages/LakeDetails";
import Sensors from "./pages/Sensors";
import Readings from "./pages/Readings";

export default function App() {
  const [backendStatus, setBackendStatus] = useState("checking");
  const [activeSection, setActiveSection] = useState("Dashboard");

  const [lakes, setLakes] = useState([]);
  const [lakesLoading, setLakesLoading] = useState(true);
  const [lakesError, setLakesError] = useState(null);

  const [sensors, setSensors] = useState([]);
  const [sensorsLoading, setSensorsLoading] = useState(false);
  const [sensorsError, setSensorsError] = useState(null);
  const [selectedSensor, setSelectedSensor] = useState(null);
  const [sensorDetails, setSensorDetails] = useState(null);
  const [sensorDetailsLoading, setSensorDetailsLoading] = useState(false);
  const [sensorDetailsError, setSensorDetailsError] = useState(null);

  const [selectedLake, setSelectedLake] = useState(null);
  const [lakeDetails, setLakeDetails] = useState(null);
  const [lakeDetailsLoading, setLakeDetailsLoading] = useState(false);
  const [lakeDetailsError, setLakeDetailsError] = useState(null);

  const [latestReading, setLatestReading] = useState(null);
  const [latestLoading, setLatestLoading] = useState(false);
  const [latestError, setLatestError] = useState(null);
  const [latestRefreshKey, setLatestRefreshKey] = useState(0);

  const [readingsPage, setReadingsPage] = useState(1);
  const [readingsRefreshKey, setReadingsRefreshKey] = useState(0);
  const [readingsData, setReadingsData] = useState({
    items: [],
    total: 0,
    pages: 0,
    size: 5,
  });
  const [readingsLoading, setReadingsLoading] = useState(false);
  const [readingsError, setReadingsError] = useState(null);

  const [lakePage, setLakePage] = useState(1);
  const [lakeRefreshKey, setLakeRefreshKey] = useState(0);
  const [lakeReadingsData, setLakeReadingsData] = useState({
    items: [],
    total: 0,
    pages: 0,
    size: 5,
  });
  const [lakeReadingsLoading, setLakeReadingsLoading] = useState(false);
  const [lakeReadingsError, setLakeReadingsError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    getHealth()
      .then(() => !cancelled && setBackendStatus("online"))
      .catch(() => !cancelled && setBackendStatus("offline"));
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    let cancelled = false;
    getLakes()
      .then((data) => {
        if (!cancelled) setLakes(data);
      })
      .catch((err) => {
        if (!cancelled) setLakesError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLakesLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, []);

  useEffect(() => {
    if (activeSection !== "Sensors") return;
    let cancelled = false;
    setSensorsLoading(true);
    setSensorsError(null);
    getSensors()
      .then((data) => {
        if (!cancelled) setSensors(data);
      })
      .catch((err) => {
        if (!cancelled) setSensorsError(err.message);
      })
      .finally(() => {
        if (!cancelled) setSensorsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeSection]);

  useEffect(() => {
    if (activeSection !== "Dashboard" || lakes.length === 0) return;
    let cancelled = false;
    const load = async () => {
      setLatestLoading(true);
      setLatestError(null);
      try {
        const data = await getLatestReading(lakes[0].lake_id);
        if (!cancelled) setLatestReading(data);
      } catch (err) {
        if (!cancelled) {
          setLatestReading(null);
          setLatestError(err.message || "Unable to load latest reading.");
        }
      } finally {
        if (!cancelled) setLatestLoading(false);
      }
    };
    load();
    const timer = setInterval(load, 5 * 60 * 1000);
    return () => {
      cancelled = true;
      clearInterval(timer);
    };
  }, [activeSection, lakes, latestRefreshKey]);

  useEffect(() => {
    if (activeSection !== "Readings") return;
    let cancelled = false;
    setReadingsLoading(true);
    setReadingsError(null);
    getReadings(readingsPage, 5)
      .then((data) => {
        if (!cancelled) setReadingsData(data);
      })
      .catch((err) => {
        if (!cancelled) setReadingsError(err.message);
      })
      .finally(() => {
        if (!cancelled) setReadingsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [activeSection, readingsPage, readingsRefreshKey]);

  useEffect(() => {
    if (!selectedLake) return;
    let cancelled = false;
    setLakeReadingsLoading(true);
    setLakeReadingsError(null);
    getLakeReadings(selectedLake.lake_id, lakePage, 5)
      .then((data) => {
        if (!cancelled) setLakeReadingsData(data);
      })
      .catch((err) => {
        if (!cancelled) setLakeReadingsError(err.message);
      })
      .finally(() => {
        if (!cancelled) setLakeReadingsLoading(false);
      });
    return () => {
      cancelled = true;
    };
  }, [selectedLake, lakePage, lakeRefreshKey]);

  async function openLake(lake) {
    setSelectedLake(lake);
    setSelectedSensor(null);
    setLakeDetails(null);
    setLakeDetailsError(null);
    setLakeDetailsLoading(true);
    setLakePage(1);
    setLakeReadingsData({ items: [], total: 0, pages: 0, size: 5 });
    try {
      setLakeDetails(await getLake(lake.lake_id));
    } catch (err) {
      setLakeDetailsError(err.message);
    } finally {
      setLakeDetailsLoading(false);
    }
  }

  async function openSensor(sensor) {
    setSelectedSensor(sensor);
    setSelectedLake(null);
    setSensorDetails(null);
    setSensorDetailsError(null);
    setSensorDetailsLoading(true);
    try {
      setSensorDetails(await getSensor(sensor.sensor_id));
    } catch (err) {
      setSensorDetailsError(err.message);
    } finally {
      setSensorDetailsLoading(false);
    }
  }

  function goBack() {
    if (selectedLake) {
      setSelectedLake(null);
      setLakeDetails(null);
      setActiveSection("Lakes");
    }
    if (selectedSensor) {
      setSelectedSensor(null);
      setSensorDetails(null);
      setActiveSection("Sensors");
    }
  }

  function navigate(section) {
    goBack();
    setActiveSection(section);
  }

  const pageTitle = selectedLake
    ? "Lake Details"
    : selectedSensor
      ? "Sensor Details"
      : activeSection === "Dashboard"
        ? "Overview"
        : activeSection;

  return (
    <div className="min-h-screen bg-slate-100 text-slate-900 md:flex">
      <Navbar activeSection={activeSection} onNavigate={navigate} />
      <main className="min-w-0 flex-1 p-5 md:p-8">
        <header className="mb-8">
          <p className="text-sm font-medium text-teal-700">WATER MONITORING</p>
          <h1 className="mt-2 text-3xl font-bold">{pageTitle}</h1>
          <p className="mt-2 text-slate-500">
            Monitor lakes and explore your water data.
          </p>
          <div className="mt-4">
            <span
              className={`rounded-full px-3 py-1 text-sm font-medium ${backendStatus === "online" ? "bg-green-100 text-green-700" : backendStatus === "offline" ? "bg-red-100 text-red-700" : "bg-slate-200 text-slate-700"}`}
            >
              {backendStatus === "checking"
                ? "Checking backend..."
                : backendStatus === "online"
                  ? "● Backend Online"
                  : "● Backend Offline"}
            </span>
          </div>
        </header>

        {selectedLake ? (
          <LakeDetails
            lake={selectedLake}
            details={lakeDetails}
            detailsLoading={lakeDetailsLoading}
            detailsError={lakeDetailsError}
            readings={lakeReadingsData}
            readingsLoading={lakeReadingsLoading}
            readingsError={lakeReadingsError}
            page={lakePage}
            onPageChange={setLakePage}
            onRefresh={() => setLakeRefreshKey((key) => key + 1)}
            onBack={goBack}
          />
        ) : selectedSensor ? (
          <section className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm">
            <button
              onClick={goBack}
              className="mb-5 text-sm font-medium text-teal-700 hover:text-teal-900"
            >
              ← Back to sensors
            </button>
            <h2 className="text-2xl font-bold">{selectedSensor.sensor_id}</h2>
            <p className="mt-1 text-sm text-slate-500">
              Connected lake: {selectedSensor.lake_id}
            </p>
            {sensorDetailsLoading && (
              <p className="mt-5 text-slate-500">Loading sensor details...</p>
            )}
            {sensorDetailsError && (
              <p className="mt-5 rounded-lg bg-red-50 p-4 text-red-700">
                Could not load sensor details: {sensorDetailsError}
              </p>
            )}
            {sensorDetails && (
              <div className="mt-6 grid gap-4 sm:grid-cols-2">
                {Object.entries({
                  "Database ID": sensorDetails.id,
                  "Sensor ID": sensorDetails.sensor_id,
                  "Lake ID": sensorDetails.lake_id,
                  Model: sensorDetails.model,
                  "Firmware version": sensorDetails.firmware_version,
                  "Installation date": sensorDetails.installation_date,
                  "Created at": sensorDetails.created_at,
                }).map(([label, value]) => (
                  <div
                    key={label}
                    className="min-w-0 rounded-lg bg-slate-50 p-4"
                  >
                    <p className="text-sm text-slate-500">{label}</p>
                    <p className="mt-1 break-words font-medium">
                      {value ?? "Not available"}
                    </p>
                  </div>
                ))}
              </div>
            )}
          </section>
        ) : activeSection === "Dashboard" ? (
          <Dashboard
            lakes={lakes}
            loading={lakesLoading}
            error={lakesError}
            latestReading={latestReading}
            latestLoading={latestLoading}
            latestError={latestError}
            onRefreshLatest={() => setLatestRefreshKey((key) => key + 1)}
            onLakeClick={openLake}
          />
        ) : activeSection === "Lakes" ? (
          <Lakes
            lakes={lakes}
            loading={lakesLoading}
            error={lakesError}
            onLakeClick={openLake}
          />
        ) : activeSection === "Sensors" ? (
          <Sensors
            sensors={sensors}
            loading={sensorsLoading}
            error={sensorsError}
            onSensorClick={openSensor}
          />
        ) : activeSection === "Readings" ? (
          <Readings
            data={readingsData}
            loading={readingsLoading}
            error={readingsError}
            page={readingsPage}
            onPageChange={setReadingsPage}
            onRefresh={() => {
              setReadingsPage(1);
              setReadingsRefreshKey((key) => key + 1);
            }}
          />
        ) : null}
      </main>
    </div>
  );
}
