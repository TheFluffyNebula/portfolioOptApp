import Select from '../components/ResourceSelect';
import Input from '@/components/Input';
import TransmissionCapSelect from '@/components/TransmissionCapSelect';
import YearSelect from '@/components/YearSelect';
import api from '../api';
import { useEffect, useState } from 'react';
import PercentLoader from '@/components/PercentLoader';

const SectionCard = ({ title, children }: { title: string; children: React.ReactNode }) => (
    <div
        className="w-full rounded-xl p-6 mb-5"
        style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
    >
        <div className="flex items-center gap-2.5 mb-5">
            <span className="block w-0.5 h-4 rounded-full flex-shrink-0" style={{ background: 'var(--accent)' }} />
            <span className="text-sm font-semibold" style={{ color: 'var(--foreground)' }}>{title}</span>
        </div>
        {children}
    </div>
);

const Prototype = () => {
    const [useApiData, setUseApiData] = useState({
        wind: [],
        wave: [],
        kite: [],
        coaxial: [],
        transmission: ['Transmission/Transmission_300MW.npz'],
        max_system_radius: 30,
        lcoe_max: 120,
        lcoe_min: 100,
        lcoe_step: 2,
        start_year: 2007,
        end_year: 2007,
        max_wind: 1,
        min_wind: 1,
        max_kite: 1,
        min_kite: 1,
        max_wave: 0,
        min_wave: 0,
        max_coaxial: 0,
        min_coaxial: 0,
        WindTurbinesPerSite: 4,
        WindResolutionKm: 2,
        KiteTurbinesPerSite: 390,
        WaveTurbinesPerSite: 300,
        CoaxialTurbinesPerSite: 390,
        lat_start: 0,
        lat_end: 0,
        lon_start: 0,
        lon_end: 0,
    });

    const STATE_RANGES: Record<string, { lat: [number, number]; lon: [number, number] }> = {
        fl: { lat: [24.2, 31.0], lon: [-81, -65] },
        ga: { lat: [30.6, 32.2], lon: [-81, -65] },
        sc: { lat: [32.0, 34.0], lon: [-81, -65] },
        nc: { lat: [33.7, 36.6], lon: [-81, -65] },
        va: { lat: [36.4, 38.2], lon: [-81, -65] },
        md: { lat: [38.0, 38.6], lon: [-81, -65] },
        de: { lat: [38.4, 39.5], lon: [-81, -65] },
        nj: { lat: [38.8, 41.0], lon: [-81, -65] },
        ny: { lat: [40.4, 41.5], lon: [-81, -65] },
        ct: { lat: [41.2, 41.5], lon: [-81, -65] },
        ri: { lat: [41.1, 41.5], lon: [-81, -65] },
        ma: { lat: [41.1, 42.9], lon: [-81, -65] },
        nh: { lat: [42.8, 43.3], lon: [-81, -65] },
        me: { lat: [43.0, 45.5], lon: [-81, -65] },
        custom: { lat: [0, 0], lon: [0, 0] },
    };

    const [files, setFiles] = useState([]);
    const [state, setState] = useState({ load: false, value: 0 });
    const [imgSrc, setImgSrc] = useState("");
    const [coords, setCoords] = useState({ latStart: 0, latEnd: 0, lonStart: 0, lonEnd: 0 });

    useEffect(() => {
        console.log(useApiData);
    }, [useApiData]);

    useEffect(() => {
        console.log(state);
    }, [state]);

    useEffect(() => {
        setUseApiData(prev => ({
            ...prev,
            lat_start: coords.latStart,
            lat_end: coords.latEnd,
            lon_start: coords.lonStart,
            lon_end: coords.lonEnd,
        }));
    }, [coords]);

    const handleChange = (e: any) => {
        const selectedFiles = Array.from(e.target.files) as File[];
        setFiles(selectedFiles);
        const newKitePaths = selectedFiles
            .filter((item: File) => item.name.includes("PowerTimeSeriesKite"))
            .map((item: File) => "OceanCurrent/" + item.name);
        if (newKitePaths.length > 0) {
            setUseApiData(prev => ({ ...prev, kite: [...prev.kite, ...newKitePaths] }));
        }
    };

    const handleUpload = async () => {
        if (!files || files.length === 0) return;
        const formData = new FormData();
        files.forEach(file => formData.append("files", file));
        const response = await api.resourceUpload(formData);
        console.log(response);
    };

    const handleWindDownload = async () => {
        if (useApiData.WindResolutionKm !== 2) {
            const data = await api.generateWindBinaries({
                "WindTurbine": [],
                "ResolutionKm": useApiData.WindResolutionKm,
            });
            console.log(data);
            if (data.status === 200) setState({ load: true, value: 10 });
        }
        const data = await api.windInputGeneration({
            "wind": useApiData.wind,
            "min_year": useApiData.start_year,
            "max_year": useApiData.end_year,
        });
        console.log(data);
        if (data.status === 200) setState({ load: true, value: 30 });
    };

    const handleKiteDownload = async () => {
        const data = await api.kiteInputGeneration({
            "kite": useApiData.kite,
            "min_year": useApiData.start_year,
            "max_year": useApiData.end_year,
        });
        console.log(data);
        if (data.status === 200) setState({ load: true, value: 40 });
    };

    const handleWaveDownload = async () => {
        const data = await api.waveInputGeneration({
            "wave": useApiData.wave,
            "min_year": useApiData.start_year,
            "max_year": useApiData.end_year,
        });
        console.log(data);
        if (data.status === 200) setState({ load: true, value: 50 });
    };

    const handleOnClick = async () => {
        await handleWindDownload();
        await handleKiteDownload();
        await handleWaveDownload();
        const data = await api.portfolioOptimization(useApiData);
        console.log(data);
        return data.data.save_path;
    };

    const postClickHandle = async (path: string) => {
        const response = await api.portfolioPlots({ portfolio: path });
        const imageBlob = new Blob([response.data], { type: 'image/png' });
        setImgSrc(URL.createObjectURL(imageBlob));
    };

    const handlePresetChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
        const range = STATE_RANGES[e.target.value];
        if (range) {
            setCoords({
                latStart: range.lat[0],
                latEnd: range.lat[1],
                lonStart: range.lon[0],
                lonEnd: range.lon[1],
            });
        }
    };

    const handleInputChange = (field: keyof typeof coords, value: string) => {
        setCoords(prev => ({ ...prev, [field]: parseFloat(value) || 0 }));
    };

    return (
        <div className="max-w-2xl mx-auto w-full px-4 py-10">

            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold mb-1.5" style={{ color: 'var(--foreground)' }}>
                    Portfolio Optimizer
                </h1>
                <p className="text-sm" style={{ color: 'var(--muted)' }}>
                    Configure parameters and generate efficient frontiers
                </p>
            </div>

            {/* Progress */}
            {state.load && (
                <div
                    className="w-full mb-5 rounded-xl p-5"
                    style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
                >
                    <div className="flex items-center justify-between mb-3">
                        <span className="text-xs font-medium" style={{ color: 'var(--muted)' }}>
                            Running optimization
                        </span>
                        <span className="text-xs font-semibold tabular-nums" style={{ color: 'var(--accent)' }}>
                            {state.value}%
                        </span>
                    </div>
                    <PercentLoader width={state.value} />
                </div>
            )}

            {/* Resources */}
            <SectionCard title="Resources">
                <Select state={useApiData} setState={setUseApiData} />
                <div className="mt-5">
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                        Upload custom resource files
                    </label>
                    <input
                        id="multiple_files"
                        type="file"
                        multiple
                        onChange={handleChange}
                        className="block w-full text-xs rounded-lg cursor-pointer px-3 py-2 focus:outline-none"
                        style={{
                            background: 'var(--surface-2)',
                            border: '1px solid rgba(255,255,255,0.08)',
                            color: 'var(--muted)',
                        }}
                    />
                    <button
                        onClick={handleUpload}
                        className="mt-3 w-full py-2 text-sm font-semibold text-white rounded-lg transition-opacity hover:opacity-90"
                        style={{ background: 'linear-gradient(135deg, #00BF63, #00a854)' }}
                    >
                        Upload Files
                    </button>
                    {files.length > 0 && (
                        <ul className="mt-2 space-y-0.5">
                            {files.map((file: File, i) => (
                                <li key={i} className="text-xs" style={{ color: 'var(--muted)' }}>
                                    {file.name}
                                </li>
                            ))}
                        </ul>
                    )}
                </div>
            </SectionCard>

            {/* Location */}
            <SectionCard title="Location">
                <div className="mb-4">
                    <label className="block text-xs font-medium mb-1.5" style={{ color: 'var(--muted)' }}>
                        Coastal state preset
                    </label>
                    <select
                        onChange={handlePresetChange}
                        className="w-full rounded-lg px-3 py-2 text-sm focus:outline-none"
                        style={{
                            background: 'var(--surface-2)',
                            border: '1px solid rgba(255,255,255,0.08)',
                            color: 'var(--foreground)',
                        }}
                    >
                        <option value="custom">Custom</option>
                        <option value="fl">Florida</option>
                        <option value="ga">Georgia</option>
                        <option value="sc">South Carolina</option>
                        <option value="nc">North Carolina</option>
                        <option value="va">Virginia</option>
                        <option value="md">Maryland</option>
                        <option value="de">Delaware</option>
                        <option value="nj">New Jersey</option>
                        <option value="ny">New York</option>
                        <option value="ct">Connecticut</option>
                        <option value="ri">Rhode Island</option>
                        <option value="ma">Massachusetts</option>
                        <option value="nh">New Hampshire</option>
                        <option value="me">Maine</option>
                    </select>
                </div>
                <div className="grid grid-cols-2 gap-4">
                    <Input label="Latitude Start" value={coords.latStart} onChange={(e) => handleInputChange('latStart', e.target.value)} step="0.01" type="number" curr="°" />
                    <Input label="Latitude End" value={coords.latEnd} onChange={(e) => handleInputChange('latEnd', e.target.value)} step="0.01" type="number" curr="°" />
                    <Input label="Longitude Start" value={coords.lonStart} onChange={(e) => handleInputChange('lonStart', e.target.value)} step="0.01" type="number" curr="°" />
                    <Input label="Longitude End" value={coords.lonEnd} onChange={(e) => handleInputChange('lonEnd', e.target.value)} step="0.01" type="number" curr="°" />
                </div>
            </SectionCard>

            {/* Technical Parameters */}
            <SectionCard title="Technical Parameters">
                <div className="grid grid-cols-2 gap-4">
                    <TransmissionCapSelect state={useApiData} setState={setUseApiData} />
                    <Input label="Max Trans. System Radius" type="number" step="0.01" placeholder="30" curr="mi" state={useApiData} setState={setUseApiData} />

                    {useApiData.wind.length > 0 && <Input label="Number of Wind Devices / Resource" type="number" step="1" placeholder="4" curr="" state={useApiData} setState={setUseApiData} />}
                    {useApiData.wind.length > 0 && <Input label="Number of Wind Devices / sq. km" step="1" type="number" placeholder="2" curr="" state={useApiData} setState={setUseApiData} />}

                    {useApiData.kite.length > 0 && <Input label="Number of Kite Devices / Resource" type="number" step="1" placeholder="390" curr="" state={useApiData} setState={setUseApiData} />}
                    {useApiData.kite.length > 0 && <Input label="Number of Kite Devices / sq. km" step="1" type="number" placeholder="0" curr="" state={useApiData} setState={setUseApiData} />}

                    {useApiData.wave.length > 0 && <Input label="Number of Wave Devices / Resource" type="number" step="1" placeholder="300" curr="" state={useApiData} setState={setUseApiData} />}
                    {useApiData.wave.length > 0 && <Input label="Number of Wave Devices / sq. km" step="1" type="number" placeholder="0" curr="" state={useApiData} setState={setUseApiData} />}

                    {useApiData.coaxial.length > 0 && <Input label="Number of Coaxial Devices / Resource" type="number" step="1" placeholder="390" curr="" state={useApiData} setState={setUseApiData} />}
                    {useApiData.coaxial.length > 0 && <Input label="Number of Coaxial Devices / sq. km" step="1" type="number" placeholder="0" curr="" state={useApiData} setState={setUseApiData} />}

                    <YearSelect label="Analysis year from" state={useApiData} setState={setUseApiData} start={true} />
                    <YearSelect label="Analysis year to" state={useApiData} setState={setUseApiData} start={false} />
                    <Input label="Distance from Shore" step="0.01" type="number" placeholder="0.0" curr="mi" state={useApiData} setState={setUseApiData} />
                    <Input label="Max Water Depth" type="number" step="0.01" placeholder="0.0" curr="mi" state={useApiData} setState={setUseApiData} />
                    <Input label="LCOE Min" type="number" step="1" placeholder="100" curr="$/MWh" state={useApiData} setState={setUseApiData} />
                    <Input label="LCOE Max" type="number" step="1" placeholder="120" curr="$/MWh" state={useApiData} setState={setUseApiData} />
                    <Input label="LCOE Step Size" type="number" step="1" placeholder="2" curr="" state={useApiData} setState={setUseApiData} />
                </div>
            </SectionCard>

            {/* Generate */}
            <button
                onClick={async () => {
                    setState({ load: true, value: 0 });
                    const path = await handleOnClick();
                    setState({ load: false, value: 100 });
                    await postClickHandle(path);
                }}
                className="w-full py-3.5 text-sm font-semibold text-white rounded-xl transition-all hover:opacity-90 hover:scale-[1.005]"
                style={{
                    background: 'linear-gradient(135deg, #00BF63, #00a854)',
                    boxShadow: '0 0 24px rgba(0,191,99,0.2)',
                }}
            >
                Generate Efficient Frontiers →
            </button>

            {imgSrc && (
                <div className="mt-8 rounded-xl overflow-hidden" style={{ border: '1px solid var(--border)' }}>
                    <img src={imgSrc} className="w-full" alt="Optimization results" />
                </div>
            )}
        </div>
    );
};

export default Prototype;
