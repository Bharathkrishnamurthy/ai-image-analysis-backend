return (
  <div className="mt-8 max-w-xl mx-auto bg-gray-900 p-6 rounded-xl">
    <h2 className="text-xl font-bold mb-3">Results</h2>

    <img src={result.image_url} className="rounded mb-4" />

    {result.result.objects.map((obj, i) => (
      <div key={i} className="flex justify-between">
        <span>{obj.object}</span>
        <span>{obj.confidence}</span>
      </div>
    ))}
  </div>
);