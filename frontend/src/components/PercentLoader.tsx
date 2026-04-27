import React from 'react';

interface PercentLoaderInterface {
    width: number;
}

const PercentLoader = ({ width }: PercentLoaderInterface) => {
    return (
        <div className="w-full h-1.5 rounded-full overflow-hidden" style={{ background: 'var(--surface-2)' }}>
            <div
                className="h-full rounded-full transition-all duration-500 ease-out"
                style={{
                    width: `${width}%`,
                    background: 'linear-gradient(90deg, #00BF63, #38BDF8)',
                }}
            />
        </div>
    );
};

export default PercentLoader;
