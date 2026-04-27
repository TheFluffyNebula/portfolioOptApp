import Link from "next/link";

type AboutCardProps = {
    title: string
    img_path: string
    info: string
    redirect: string
}

const DownloadCard = ({ title, img_path, info, redirect }: AboutCardProps) => {
    return (
        <div
            className="rounded-xl overflow-hidden transition-all hover:translate-y-[-2px]"
            style={{ background: 'var(--surface)', border: '1px solid var(--border)' }}
        >
            <Link href="#">
                <img className="w-full object-cover" src={img_path} alt={title} />
            </Link>
            <div className="p-5">
                <Link href="#">
                    <h5 className="mb-2 text-base font-semibold" style={{ color: 'var(--foreground)' }}>
                        {title}
                    </h5>
                </Link>
                <p className="mb-4 text-sm leading-relaxed" style={{ color: 'var(--muted)' }}>
                    {info}
                </p>
                <Link
                    href={redirect}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 text-xs font-semibold text-white rounded-md transition-opacity hover:opacity-90"
                    style={{ background: 'linear-gradient(135deg, #00BF63, #00a854)' }}
                >
                    Explore
                    <svg className="w-3 h-3" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 14 10">
                        <path stroke="currentColor" strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M1 5h12m0 0L9 1m4 4L9 9" />
                    </svg>
                </Link>
            </div>
        </div>
    );
};

export default DownloadCard;
