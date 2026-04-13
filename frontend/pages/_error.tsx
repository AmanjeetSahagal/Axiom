import type { NextPageContext } from "next";

type ErrorPageProps = {
  statusCode?: number;
};

function ErrorPage({ statusCode }: ErrorPageProps) {
  return (
    <main className="mx-auto flex min-h-screen max-w-3xl items-center justify-center px-6 py-16">
      <section className="rounded-[32px] border border-black/5 bg-white/85 p-10 shadow-panel">
        <p className="text-sm uppercase tracking-[0.3em] text-ember">Frontend Error</p>
        <h1 className="mt-3 font-display text-4xl text-ink">
          {statusCode ? `Error ${statusCode}` : "Unexpected error"}
        </h1>
        <p className="mt-4 text-slate-600">
          The page could not be rendered. Refresh once and retry the action.
        </p>
      </section>
    </main>
  );
}

ErrorPage.getInitialProps = ({ res, err }: NextPageContext) => {
  const statusCode = res?.statusCode ?? err?.statusCode ?? 500;
  return { statusCode };
};

export default ErrorPage;
